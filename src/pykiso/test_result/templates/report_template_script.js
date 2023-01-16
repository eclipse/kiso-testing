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
