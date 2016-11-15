for i in open('/tmp/out.csv').readlines():
    personid, orgid = i.split('\t')
    orgid = orgid.strip('\n')
    if not (personid.isdigit() and orgid.isdigit()):
        continue
    try:
        person = Person.objects.get(pk=personid)
        organization = Organization.objects.get(pk=orgid)
    except Person.DoesNotExist:
        continue
    except Organization.DoesNotExist:
        continue
    organization.primary_contact_person = person
    organization.save()
