// Open all details elements to show the anchor
function dd_open_details(event) {
    const url = new URL(window.location);
    if (url.hash && url.hash != "#") {
        const anchor_element = document.querySelector(url.hash);
        if (anchor_element) {
            let element = anchor_element;
            while (element.parentNode) {
                element = element.parentNode;
                if (element.tagName == "DETAILS") {
                    element.open = true;
                }
            }
            anchor_element.scrollIntoView();
        }
    }
}
// Open details elements when we click a link on the same page, or when the page loads
window.addEventListener("hashchange", dd_open_details);
window.addEventListener("load", dd_open_details);
window.addEventListener("load", (event)=>{
    // Links inside summary elements open in a new tab
    for (var element of document.querySelectorAll(
            "a.dd-dynamic, a.dd-static, a.dd-constant, a.dd_data_type, a.errorbar")) {
        element.target = "_blank";
    }
})
