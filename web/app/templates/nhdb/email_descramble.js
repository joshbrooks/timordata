/**
 * Created by josh on 8/11/15.
 */

/* {% comment %}
 * Original code:
 *
 * @returns {string}

    String.prototype.reverse = function () {
        return this.split("").reverse().join("");
    };
    String.prototype.dotat = function () {
        return this.replace(/ at /gi, '@').replace(/ dot /gi ,'.')};

    String.prototype.rot13 = function () {
        return this.replace(/[a-zA-Z]/gi, function (c) {
            return String.fromCharCode((c <= "Z" ? 90 : 122) >= (c = c.charCodeAt(0) + 13) ? c : c - 26);
        });
    };
    $(document).ready(function(){
        // Decode emails in any column with 'email' class when a 'button.showliame' is clicked
        // Click an encoded email address to show it
        $('button.showliame').on('click', function(){
            var table = $('.email').parents('table:first')
            var index = $('.email').parent().children().index( $('.email') )
            $(this).addClass('disabled')
            table.find('tbody tr').each(function(){
                var i = $(this).children('td')[index];
                $(i).css({color:'green'});
                $(i).text($(i).text().reverse().rot13().dotat())
            })
        });

    });
    // The equivalent code, obfuscated, is shoen below
{% endcomment %}
*/
    var _0xeeb1=["\x72\x65\x76\x65\x72\x73\x65","\x70\x72\x6F\x74\x6F\x74\x79\x70\x65","","\x6A\x6F\x69\x6E","\x73\x70\x6C\x69\x74","\x64\x6F\x74\x61\x74","\x2E","\x72\x65\x70\x6C\x61\x63\x65","\x40","\x72\x6F\x74\x31\x33","\x5A","\x63\x68\x61\x72\x43\x6F\x64\x65\x41\x74","\x66\x72\x6F\x6D\x43\x68\x61\x72\x43\x6F\x64\x65","\x63\x6C\x69\x63\x6B","\x74\x61\x62\x6C\x65\x3A\x66\x69\x72\x73\x74","\x70\x61\x72\x65\x6E\x74\x73","\x2E\x65\x6D\x61\x69\x6C","\x69\x6E\x64\x65\x78","\x63\x68\x69\x6C\x64\x72\x65\x6E","\x70\x61\x72\x65\x6E\x74","\x64\x69\x73\x61\x62\x6C\x65\x64","\x61\x64\x64\x43\x6C\x61\x73\x73","\x74\x64","\x67\x72\x65\x65\x6E","\x63\x73\x73","\x74\x65\x78\x74","\x65\x61\x63\x68","\x74\x62\x6F\x64\x79\x20\x74\x72","\x66\x69\x6E\x64","\x6F\x6E","\x62\x75\x74\x74\x6F\x6E\x2E\x73\x68\x6F\x77\x6C\x69\x61\x6D\x65","\x72\x65\x61\x64\x79"];String[_0xeeb1[1]][_0xeeb1[0]]=function(){return this[_0xeeb1[4]](_0xeeb1[2])[_0xeeb1[0]]()[_0xeeb1[3]](_0xeeb1[2])};String[_0xeeb1[1]][_0xeeb1[5]]=function(){return this[_0xeeb1[7]](/ at /gi,_0xeeb1[8])[_0xeeb1[7]](/ dot /gi,_0xeeb1[6])};String[_0xeeb1[1]][_0xeeb1[9]]=function(){return this[_0xeeb1[7]](/[a-zA-Z]/gi,function(_0x3e4cx1){return String[_0xeeb1[12]]((_0x3e4cx1<=_0xeeb1[10]?90:122)>=(_0x3e4cx1=_0x3e4cx1[_0xeeb1[11]](0)+13)?_0x3e4cx1:_0x3e4cx1-26)})};$(document)[_0xeeb1[31]](function(){$(_0xeeb1[30])[_0xeeb1[29]](_0xeeb1[13],function(){var _0x3e4cx2=$(_0xeeb1[16])[_0xeeb1[15]](_0xeeb1[14]);var _0x3e4cx3=$(_0xeeb1[16])[_0xeeb1[19]]()[_0xeeb1[18]]()[_0xeeb1[17]]($(_0xeeb1[16]));$(this)[_0xeeb1[21]](_0xeeb1[20]);_0x3e4cx2[_0xeeb1[28]](_0xeeb1[27])[_0xeeb1[26]](function(){var _0x3e4cx4=$(this)[_0xeeb1[18]](_0xeeb1[22])[_0x3e4cx3];$(_0x3e4cx4)[_0xeeb1[24]]({color:_0xeeb1[23]});$(_0x3e4cx4)[_0xeeb1[25]]($(_0x3e4cx4)[_0xeeb1[25]]()[_0xeeb1[0]]()[_0xeeb1[9]]()[_0xeeb1[5]]());});})});