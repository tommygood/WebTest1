<?php
// get the current view
$counter = file_get_contents("https://tommygood.github.io/WebTest1/index.html");
 
if (!isset($_COOKIE['article_read'])) {
    setcookie("article_read", 1, time()+10);
    $counter++;
    $fp = fopen("https://tommygood.github.io/WebTest1/index.html, "w");
    fwrite($fp, $counter);
    fclose($fp);
}
 
echo "document.write('" . $counter . "');";
?>