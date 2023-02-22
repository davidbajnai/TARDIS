<?php
include '../model/model.php';
$listOfCourses = get_courses();
$semester = ( !empty($_GET['semester']) ? $_GET['semester'] : '' );
$courseName = find_course_by_semester( $semester );

include '../viewer/viewer.php';