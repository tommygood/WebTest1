function Main(d) {
    var v = document.getElementById('para');
    var myHeading = document.querySelector('h1');
    var a = "1";
    var n = document.getElementById('aaa');
    //alert(n.value);
    // myHeading.textContent = n.value;
    // myHeading.textContent = v.innerHTML;
    console.log("a");
}
function ChangeWeb() {
    var myHeading = document.querySelector('h1');
    var n = document.getElementById('aaa');
    if (n.value == "王冠權") {
        window.location.href='https://tommygood.github.io/WebTest1/index.html';
    }
    else
        myHeading.textContent = "這誰";
}
