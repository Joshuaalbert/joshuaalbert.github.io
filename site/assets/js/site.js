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
      scope.addEventListener("pointerdown", function (event) {
        var target = event.target.closest ? event.target.closest(".defocus-item") : null;
        if (target && scope.contains(target)) setFocus(target);
      });
      scope.addEventListener("pointerleave", clearFocus);
      items.forEach(function (item) {
        item.addEventListener("focusin", function () { setFocus(item); });
        item.addEventListener("focusout", clearFocus);
      });
    });
  }

  function initAlbumPreviews() {
    if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    document.querySelectorAll(".album-preview").forEach(function (preview) {
      var frames = Array.prototype.slice.call(preview.querySelectorAll(".album-preview-frame"));
      if (frames.length < 2) return;
      var index = 0;
      frames.forEach(function (frame, frameIndex) {
        frame.classList.toggle("is-visible", frameIndex === 0);
      });
      window.setInterval(function () {
        frames[index].classList.remove("is-visible");
        window.setTimeout(function () {
          index = (index + 1) % frames.length;
          frames[index].classList.add("is-visible");
        }, 1200);
      }, 6200);
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

  function initPhotoNavigation() {
    var viewer = document.querySelector(".photo-viewer");
    if (!viewer) return;
    var photos = Array.prototype.slice.call(document.querySelectorAll(".viewer-photo-data"));
    var currentIndex = parseInt(viewer.getAttribute("data-current-index") || "0", 10);
    var albumTitle = viewer.getAttribute("data-album-title") || "";
    var fullscreenChangedPhoto = false;

    function currentPhoto() {
      return photos[currentIndex] ? photos[currentIndex].dataset : null;
    }

    function photoAt(index) {
      return photos[index] ? photos[index].dataset : null;
    }

    function setPhoto(index, fromFullscreen) {
      var data = photoAt(index);
      if (!data) return false;
      currentIndex = index;
      viewer.setAttribute("data-current-index", String(index));

      var source = viewer.querySelector(".viewer-image source");
      var image = viewer.querySelector(".viewer-image img");
      if (source && data.fullWebp) source.setAttribute("srcset", data.fullWebp);
      if (source && !data.fullWebp) source.removeAttribute("srcset");
      if (image) {
        image.setAttribute("src", data.full);
        image.setAttribute("alt", data.alt || data.title || "");
      }

      var title = viewer.querySelector(".photo-meta h1");
      var detail = viewer.querySelector(".photo-meta p:first-of-type");
      var exif = viewer.querySelector(".photo-exif");
      var description = viewer.querySelector(".photo-description");
      if (title) title.textContent = data.title || "";
      if (detail) detail.textContent = (data.date || "") + " · " + (data.location || "");
      if (exif) {
        exif.textContent = data.exif || "";
        exif.hidden = !data.exif;
      }
      if (description) {
        description.textContent = data.description || "";
        description.hidden = !data.description;
      }
      if (data.url) window.history.replaceState(null, "", data.url);
      if (data.giscusTitle) document.title = data.giscusTitle;
      if (fromFullscreen) fullscreenChangedPhoto = true;
      return true;
    }

    function navigateBy(delta) {
      var nextIndex = currentIndex + delta;
      var data = photoAt(nextIndex);
      if (!data) return;
      if (document.fullscreenElement) {
        setPhoto(nextIndex, true);
        return;
      }
      window.location.assign(data.url);
    }

    window.addEventListener("keydown", function (event) {
      var target = event.target;
      var tagName = target && target.tagName ? target.tagName.toLowerCase() : "";
      if (tagName === "input" || tagName === "textarea" || target.isContentEditable) return;
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        navigateBy(-1);
      }
      if (event.key === "ArrowRight") {
        event.preventDefault();
        navigateBy(1);
      }
    }, true);

    document.addEventListener("fullscreenchange", function () {
      if (document.fullscreenElement || !fullscreenChangedPhoto) return;
      var data = currentPhoto();
      fullscreenChangedPhoto = false;
      if (data && data.url) {
        window.location.replace(data.url);
      }
    });
  }

  function initPhotoFullscreen() {
    var target = document.querySelector(".viewer-image");
    if (!target || !target.requestFullscreen) return;

    target.addEventListener("click", function () {
      if (document.fullscreenElement === target) {
        document.exitFullscreen();
      } else {
        target.requestFullscreen();
      }
    });

    document.addEventListener("fullscreenchange", function () {
      var active = document.fullscreenElement === target;
      target.setAttribute(
        "aria-label",
        active ? "Exit photo full screen" : "Open photo full screen"
      );
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      initDefocus();
      initAlbumPreviews();
      initPhotoNavigation();
      initPhotoFullscreen();
      initKatex();
    });
  } else {
    initDefocus();
    initAlbumPreviews();
    initPhotoNavigation();
    initPhotoFullscreen();
    initKatex();
  }
})();
