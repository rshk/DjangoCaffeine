## This is a coffeescript file!


onload = () ->
    el = document.getElementById('test-div-coffee')
    console.log(el);
    el.style.border = 'solid 1px #00f'
    el.style.background = '#eef'
    el.style.padding = '5px'
    el.style.margin = '5px'
    null


if addEventListener
    addEventListener('load', onload, false) #W3C
else
    attachEvent('onload', onload) #IE
