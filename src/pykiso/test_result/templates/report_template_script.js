/*
synchronize the toggling of all details elements by class name
class name is unique for each test + row combination and gets rendered in by jinja
*/
function toggleDetailsInRow(element, className) {
    element.scrollIntoView();
    isOpen = element.hasAttribute("open");
    // const className = element.classList[0];
    const detailsElements = document.getElementsByClassName(className);
    if (isOpen == true) {
        for (detail of detailsElements) {
            detail.open = true;
        }
    } else {
        for (detail of detailsElements) {
            detail.open = false;
        }
    }
}
