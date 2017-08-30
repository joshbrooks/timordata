# Copyright 2014 Joshua Brooks <josh.brooks@belun.yandex.com>
# This extension to Django models implements a 'materialised path'
# design for database tables containing hierarchical or categorised
# data.

# Examples are:
# Place codes:
#   district = '01'
#       subdistrict = '0101'
#             village = '010101'

# Question / Answer sets for a survey

from django.utils.safestring import mark_safe
from django.db import models
from django.conf import settings


class MP_Lite(models.Model):

    """Materialised Path model implementation for Django

    Inspired by Treebeard's MP_Node but designed for
    faster inserts, a single 'path' column (no depth or child counts),
    and manually assigned (mnemonic) labels.

    Attributes:
      separator (string): Character to use as a separator (suggest '.')
      steps (int): How many characters at each level

    """
    class Meta:
        abstract = True

    separator = '.'
    steps = 2

    @classmethod
    def getfromstring(cls, string):
        """ Return an object with the given path 
        """
        return cls.objects.get(path=cls.separatestring(string))

    @classmethod
    def separatestring(cls, string):
        """ Convert a string like 'ailail' to 'AIL.AIL'
        """
        s = string.upper()
        if cls.separator in s:
            # Assume this already is pathformatted
            return s  # cls.objects.get(path=s)
        path = cls.separator.join([string[i:i + cls.steps]
                                   for i in range(0, len(s), cls.steps)])
        return path

    def pathstring(self):
        return self.path.replace(self.separator, '').upper()

    def lowerpathstring(self):
        return self.pathstring().lower()

    def path_display(self):
        """ Synonym for lowerpathstring
        """
        return self.lowerpathstring()

    class NoParentError(Exception):
        pass

    def __unicode__(self):
        return '{} (path:{})'.format(self.name, self.path)

    path = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        """ Check that this is a root node OR that a parent node exists for it
        """

        if len(self.path) == self.__class__.steps:
            # This is a root node
            super(MP_Lite, self).save(*args, **kwargs)

        else:
            try:
                self.__class__.get_ancestor(self)
            except self.__class__.DoesNotExist:
                raise self.__class__.NoParentError(
                    'No ancestor node to %s' % self.path)

            super(MP_Lite, self).save(*args, **kwargs)

    def delete(self):
        """ Delete this node and all child nodes
        """
        self.get_descendants().delete()
        super(MP_Lite, self).delete()

    def update(self, **kwargs):
        super(MP_Lite, self).update(**kwargs)
        for s in self.get_descendants():
            s.path = self.path + s.path[len(self.path)]
            s.save()

    def move(self, new_parent):

        descendants = self.get_descendants()

        self.path = new_parent.path + self.separator + \
            self.path[len(new_parent.path) + len(self.separator):]
        self.save()

        for s in descendants:
            s.path = new_parent.path + s.separator + \
                s.path[len(new_parent.path) + len(self.separator):]
            s.save()

    @classmethod
    def get_root_nodes(cls):
        """ Return all of the lowest level nodes
        """
        return cls.objects.extra(where=["path like %s"], params=['_' * cls.steps]).all()

    @classmethod
    def level(cls, level):
        where = level * cls.steps + (level - 1) * len(cls.separator)
        return cls.objects.extra(where=["path like %s"], params=['_' * where]).all()

    def _level(self):
        '''
        Count number of separators to determine level
        '''
        return self.path.count(self.separator)  # - 1

    def get_siblings(self, include_self=False):
        cls = self.__class__
        _w = ["path like %s"]
        _p = ['_' * len(self.path)]

        if include_self:
            _w[0] = _w[0] + (' AND path != %s')
            _p.append(self.path)
        return cls.objects.extra(
            where=_w,
            params=_p
        ).all()

    def get_children(self, include_self=False):

        cls = self.__class__
        _w = ["path like %s"]
        _p = [self.path + self.separator + '_' * cls.steps]

        if include_self:
            _w[0] = _w[0] + (' OR path like %s')
            _p.append(self.path)
        return cls.objects.extra(
            where=_w,
            params=_p
        ).all().order_by('path')

    def childvaluesjson(self, attr="name"):
        return mark_safe(json.dumps([i[0] for i in self.get_children().values_list(attr)]))

    def childvalueslist(self, attr="name"):
        '''
        Return a list of specified child attributes
        '''
        from django.utils.safestring import mark_safe
        return mark_safe([i[0] for i in self.get_children().values_list(attr)])

    def childnames(self):
        '''
        Return a list of child names
        '''
        return self.childvalueslist('name')

    def childpaths(self):
        '''
        Return a list of child paths
        '''

        return self.childvalueslist('path')

    def childpks(self):
        '''
        Return a list of child primary keys
        '''
        return self.childvalueslist('pk')

    def get_descendants(self, include_self=True):
        cls = self.__class__

        if include_self:
            extra = self.path + '%'
        else:
            extra = self.path + self.separator + '%'
        return cls.objects.extra(
            where=["path like %s"],
            params=[extra]
        ).all()

    def get_ancestor_path(self):
        ancestor_path = self.path[:-(self.steps + len(self.separator))]
        return ancestor_path

    def get_ancestor_list(self):
        returns = [self]
        parent = self.get_ancestor()
        while parent:
            returns.append(parent)
            parent = parent.get_ancestor()
        return returns

    def get_ancestor(self):
        try:
            return self.__class__.objects.get(path=self.get_ancestor_path())
        except self.__class__.DoesNotExist:
            return None
