// Static Semgrep rule fixtures only. Never execute this file.
function positiveFixtures(node, input, vm, source, fs) {
  // ruleid: pouch-unsafe-html-write
  node.innerHTML = input;
  // ruleid: pouch-dynamic-code
  eval(input);
  // ruleid: pouch-inline-event-attribute
  node.setAttribute('onclick', input);
  // ruleid: pouch-review-url-write
  node.href = input;
  // ruleid: pouch-review-network
  fetch(input);
  // ruleid: pouch-review-vm-boundary
  vm.runInNewContext(source, {});
  // ruleid: pouch-review-file-read
  fs.readFileSync(input, 'utf8');
}
function negativeFixtures(node, text) {
  // ok: pouch-unsafe-html-write
  node.textContent = text;
  // ok: pouch-inline-event-attribute
  node.setAttribute('aria-label', text);
}
