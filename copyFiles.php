<?php
function getFiles( $dir ){
    return array_values(array_filter(scandir($dir), function($file){
        global $dir;
        return !is_dir("{$dir}/{$file}");
    }));
}
$folderName = $_POST['folderName']; // Results/220226_084003_bottleCO2
// $folderName = '220405_194645_Refgas6';
$date = $_POST['date']; // This is the UNIX time, seconds since 1.1.1970 like 1645861203
$ymdSting = substr( $folderName, 8, 13); // 220234_183401
echo $ymdSting;

$path = '/mnt/TILDAS-CS-132/Data';
$files = getFiles( $path );

// foreach ($files as $file) {
//     if( substr($file,0,7)  == "220405_" )
//     {
//         echo "$file<br>";
//     }
// }

foreach( $files as $file )
{
    if( $file[0] == "2" && $file[6] == "_" && $file[13] == "." && ( substr($file, -3) == "str" || substr($file, -3) == "stc" ) && substr( $file, 0, 13 ) > $ymdSting  )
    {
        exec("cp /mnt/TILDAS-CS-132/Data/$file $folderName/$file");
        // echo copy( "/mnt/TILDAS-CS-132/Data/" + $file, $folderName + "/" + $file );
        echo $file . " ...OK<br />";
    }
}

// 1645861203 Results/220226_084003_bo
// copy( "/mnt/TILDAS-CS-132/Data/source.txt", $folderName + "/target.txt" );
echo "Files successfully copied to local folder.";