<?php
    $m = new Memcached();
    $m->addServer('127.0.0.1', 11211);
    // get a value
    $value = $m->get('key');
    echo $value;
    // set a value
    $m->set('key2', 'Message from PHP');
    // clean up
    $m->quit();
?>