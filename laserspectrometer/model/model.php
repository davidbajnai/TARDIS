<?php

function get_courses(){
    include '../data/data.php';
    return array_values($courses);
}

function find_course_by_semester($semester){
    include '../data/data.php';
    return ( array_key_exists($semester,$courses) ? $courses[$semester] : 'Invalid semester.' );
}