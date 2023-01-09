/*
synchronize the toggling of all details elements by class name
class name is unique for each test + row combination and gets rendered in by jinja
*/
function toggleDetailsInRow(element, className) {
    element.scrollIntoView();
    const isOpen = element.hasAttribute("open");
    const detailsElements = document.getElementsByClassName(className);
    for (detail of detailsElements) {
        detail.open = isOpen;
    }
}
