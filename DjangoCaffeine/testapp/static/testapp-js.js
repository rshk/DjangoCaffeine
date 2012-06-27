/**
 * This is a javascript file
 */
var onload = function() {
    var el = document.getElementById('test-div-js');
    el.style.border = 'solid 1px #00f';
    el.style.padding = '5px';
    el.style.margin = '5px';
};

if (window.addEventListener) {
    window.addEventListener('load', onload, false); //W3C
}
else {
    window.attachEvent('onload', onload); //IE
}

