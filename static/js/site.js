'use strict';

/** global variables: **/

/* init these: */
var navigation_menu_div, navigation_text_div, navigation_text_display;
var menu_visibility = false;

/** functions: **/

function init_variables() {
  navigation_menu_div = document.getElementById('navigation_menu');
  navigation_text_div = document.getElementById('navigation_text');
  navigation_text_display = navigation_text_div.style.display;
}

function toggle_menu_visibilty() {
  if (menu_visibility == false) {
    navigation_text_div.style.display = 'block';
    menu_visibility = true;
  } else {
    navigation_text_div.style.display = 'none';
    menu_visibility = false;
  }
}

function add_menu_listener() {
  navigation_menu_div.onclick = function() {
    toggle_menu_visibilty();
  }
}

function update_layout() {
  var menu_display = 'none';
  if (typeof getComputedStyle !== 'undefined') {
      menu_display = getComputedStyle(navigation_menu_div).display;
  } else if (typeof navigation_menu_div.currentStyle !== 'undefined') {
      menu_display = navigation_menu_div.currentStyle.display;
  }
  if (menu_display == 'none') {
    navigation_text_div.style.display = navigation_text_display;
    menu_visibility = true;
  } else {
    navigation_text_div.style.display = 'none';
    menu_visibility = false;
  } 
}

/* full screen images: */

function display_fs_img(img_src) {
  var img_div = document.getElementById("fs_img_div");
  var img_element = document.getElementById("fs_img_img");
  img_element.src = img_src;
  img_div.style.display = 'block'; 
}

function close_fs_img() {
  var img_div = document.getElementById("fs_img_div");
  var img_element = document.getElementById("fs_img_img");
  img_div.style.display = 'none';
  img_element.src = '';
}

/* add full screen image listeners: */
function load_fs_imgs() {
  var fs_imgs = document.getElementsByClassName("fs_img");
  /* for each image: */  
  for (var i = 0; i < fs_imgs.length; i++) {
    fs_imgs[i].addEventListener('click', function(e) {
      display_fs_img(e.target.attributes.src.value);
    });
  }
  /* add close listener: */
  var fs_img_close = document.getElementById("fs_img_close");
  fs_img_close.addEventListener('click', function() {
    close_fs_img();
  });
}

/* set up the page: */
function load_page() {
  init_variables();
  add_menu_listener();
  load_fs_imgs();
}

/** add listeners: **/

/* on page load: */
window.addEventListener('load', function() {
  /* set up the page ... : */
  load_page();
});

/* on page resize: */
window.addEventListener('resize', function() {
  /* update the layout: */
  update_layout();
});
