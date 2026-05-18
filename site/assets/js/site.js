(function () {
  function initDefocus() {
    var scopes = document.querySelectorAll(".defocus-scope");
    scopes.forEach(function (scope) {
      var items = Array.prototype.slice.call(scope.querySelectorAll(".defocus-item"));
      if (!items.length) return;

      function setFocus(target) {
        scope.classList.add("is-defocusing");
        items.forEach(function (item) {
          item.classList.toggle("is-focus", item === target || item.contains(target));
        });
      }

      function clearFocus() {
        scope.classList.remove("is-defocusing");
        items.forEach(function (item) {
          item.classList.remove("is-focus");
        });
      }

      scope.addEventListener("pointermove", function (event) {
        var focused = items.reduce(function (best, item) {
          var rect = item.getBoundingClientRect();
          var center = rect.top + rect.height / 2;
          var distance = Math.abs(center - event.clientY);
          if (!best || distance < best.distance) {
            return { item: item, distance: distance };
          }
          return best;
        }, null);
        if (focused) setFocus(focused.item);
      });
      scope.addEventListener("pointerleave", clearFocus);
      items.forEach(function (item) {
        item.addEventListener("focusin", function () { setFocus(item); });
        item.addEventListener("focusout", clearFocus);
      });
    });
  }

  function initKatex() {
    if (!window.renderMathInElement) return;
    window.renderMathInElement(document.body, {
      delimiters: [
        { left: "$$", right: "$$", display: true },
        { left: "\\[", right: "\\]", display: true },
        { left: "\\(", right: "\\)", display: false }
      ],
      throwOnError: false
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      initDefocus();
      initKatex();
    });
  } else {
    initDefocus();
    initKatex();
  }
})();

