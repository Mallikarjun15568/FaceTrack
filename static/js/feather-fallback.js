// Lightweight fallback for feather icons when CDN is unavailable.
// Tries to render approximate FontAwesome icons when possible, otherwise no-op to avoid errors.
(function(){
  if (typeof feather !== 'undefined') return; // real feather already present

  window.feather = {
    replace: function(opts){
      try {
        document.querySelectorAll('[data-feather]').forEach(function(el){
          var name = (el.getAttribute('data-feather') || '').trim();

          // Simple mapping from common feather names to FontAwesome classes
          var faMap = {
            'grid':'fa-th',
            'users':'fa-users',
            'camera':'fa-camera',
            'monitor':'fa-desktop',
            'check-circle':'fa-circle-check',
            'calendar':'fa-calendar',
            'bar-chart-2':'fa-chart-bar',
            'settings':'fa-gear',
            'log-out':'fa-arrow-right-from-bracket',
            'user-check':'fa-user-check',
            'user-xmark':'fa-user-slash',
            'clock':'fa-clock',
            'check-square':'fa-square-check'
          };

          var span = document.createElement('span');
          span.className = el.className || '';

          // If FontAwesome is available, use mapped icon
          var faClass = faMap[name];
          if ((typeof FontAwesome !== 'undefined') || document.querySelector('link[href*="font-awesome"], link[href*="fontawesome"], link[href*="fontawesome"]') || document.querySelector('link[href*="fontawesome"]')) {
            var i = document.createElement('i');
            i.className = 'fa ' + (faClass || 'fa-circle');
            span.appendChild(i);
          } else if (faClass) {
            var i = document.createElement('i');
            i.className = 'fa ' + faClass;
            span.appendChild(i);
          } else {
            // no icon library available; preserve original element but remove data attribute
            el.removeAttribute('data-feather');
            return;
          }

          // Preserve tooltip/title if present
          if (el.title) span.title = el.title;

          el.parentNode && el.parentNode.replaceChild(span, el);
        });
      } catch (e) {
        // swallow errors — fallback should never break the page
        console.warn('feather-fallback failed', e);
      }
    }
  };
})();
