function countCoaches() {
    xpath = "//table[@class='profile-list']/tbody/tr//a[img]"

    let results = [];
    let query = document.evaluate(xpath, document.body || document,
        null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
    for (let i = 0, length = query.snapshotLength; i < length; ++i) {
        results.push(query.snapshotItem(i));
    }

    return results.length;
}; countCoaches();

