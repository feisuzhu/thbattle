<?php

if(!defined('IN_DISCUZ')) {
	exit('Access Denied');
}


class plugin_thbattle_interconnect {
    public function global_header() {
        return '<script src="/source/plugin/thbattle_interconnect/resource/jquery-1.9.1.min.js"></script><script type="text/javascript">jq = jQuery.noConflict();</script>';
    }
}


class plugin_thbattle_interconnect_forum {
    public function index_top() {
        return file_get_contents('resource/inject.html', FILE_USE_INCLUDE_PATH);
    }

    public function viewthread_top() {
        return file_get_contents('resource/inject.html', FILE_USE_INCLUDE_PATH);
    }

    public function forumdisplay_top() {
        return file_get_contents('resource/inject.html', FILE_USE_INCLUDE_PATH);
    }
}


?>
