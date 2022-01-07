<?php
// get the current view
$counter = file_get_contents("http://127.0.0.1/index.html");
 
if (!isset($_COOKIE['article_read'])) {
    setcookie("article_read", 1, time()+10);
    $counter++;
    $fp = fopen("http://127.0.0.1/index.html, "w");
    fwrite($fp, $counter);
    fclose($fp);
}
 
echo "document.write('" . $counter . "');";
?>