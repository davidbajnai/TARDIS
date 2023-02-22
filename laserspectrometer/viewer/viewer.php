This is the course from the selected semester: <?php echo $courseName;?>.
<select name='courses'>
    <?php foreach($listOfCourses as $courseName): ?>
        <option><?=$courseName?></option>
    <?php endforeach?>
</select>