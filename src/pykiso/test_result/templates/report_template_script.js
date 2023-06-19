/**
 * synchronize the toggling of all details elements by class name
 * class name is unique for each test + row combination and gets rendered in by jinja
 * @param {HTMLDetailsElement} element the details element being toggled
 * @param {string} className class attribute of all details elements in the row
 */
function toggleDetailsInRow(element, className) {
    element.scrollIntoView();
    const isOpen = element.hasAttribute("open");
    const detailsElements = document.getElementsByClassName(className);
    for (details of detailsElements) {
        details.open = isOpen;
        isOpen ? setSummary("Click to minimize", details) : setTruncatedSummary(details);
    }
} // no-unused-vars function is used (false positive),eslint-disable-line


document.addEventListener("DOMContentLoaded", function() {
    var failButton = document.getElementById("failButton");
    failButton.addEventListener("click", function(){
    var failedDetailElements = document.querySelectorAll(".failed-test-details");
    failedDetailElements.forEach(function(details){
        toggleFailDetails(details);
    });});});

/**
 * collapse or expand all detail elements which have Fail inside the summary sting.
 */
function toggleFailDetails(detailsElement) {
    if (detailsElement.open)
    {
        detailsElement.removeAttribute("open");
        failButton.innerText = "Expand all failed tests";
    } else {
        detailsElement.setAttribute("open", "true");
        failButton.innerText = "Collapse all failed tests";
    }
}

var allButton = document.getElementById("allButton");

allButton.addEventListener("click", toggleAllDetails);

/**
 * collapse or expand all detail elements.
 */

function toggleAllDetails() {
    var detailsElements = document.querySelectorAll("details");
    if (detailsElements[0].open || detailsElements[1].open) {
        for (var i = 0; i < detailsElements.length; i++) {
            detailsElements[i].open = false;
        }
        allButton.innerText = "Expand all tests";
        failButton.innerText = "Expand all failed tests";
    } else {
        for (var i = 0; i < detailsElements.length; i++) {
            detailsElements[i].open = true;
        }
        allButton.innerText = "Collapse all tests";
        failButton.innerText = "Collapse all failed tests";
    }
}

/* helper functions */

/**
 * set the summary text of the details element
 * @param {string} content new content of the summary element
 * @param {HTMLDetailsElement} detailsElement parent of the summary being modified
 */
function setSummary(content, detailsElement) {
    const summaryElement = detailsElement.getElementsByTagName("summary")[0];
    summaryElement.innerHTML = content;
}

/**
 * same result as jinja truncate when rendering to set summary after closing
 * @param {HTMLDetailsElement} detailsElement parent of the summary being modified
 * @param {number} length length to cut the content to, default is 50
 * @returns the truncated string
 */
function setTruncatedSummary(detailsElement, length = 50) {
    const divElement = detailsElement.getElementsByTagName("div")[0];
    let shortened = divElement.textContent.trim().slice(0, length);
    shortened = shortened + "...";
    setSummary(shortened, detailsElement);
}
