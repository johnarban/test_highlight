<script>
/**
 * PlotlyHighlighting - Client-side histogram bin highlighting using Vue.js and DOM manipulation.
 * Uses BinManager to create underlying bins, then applies highlighting directly in the browser.
 * More performant than Python-based highlighting but doesn't emit hover events to Python.
 */
export default {
  

  props: {
    viewer_id: {
      type: String,
      default: ''
    },
    show: {
      type: Boolean,
      default: true
    },
    highlight: {
      type: Boolean,
      default: true
    },
    debug: {
      type: Boolean,
      default: false
    },
    
    fillColor: {
      type: String,
      default: 'rgb(0, 0, 0)'
    },
    fillOpacity: {
      type: Number,
      default: 0.5
    },
    strokeColor: {
      type: Number,
      default: 'rgb(120, 120, 255)'
    },
    strokeOpacity: {
      type: Number,
      default: 1
    },
    strokeWidth: {
      type: Number,
      default: 1
    },
    opacity: {
      type: Number,
      default: 1
    },
  },

  data() {
    return {
      el: [],                    // Array of histogram bar elements
      hoverDuration: 0,          // Tracks hover time
      debounceTimeout: null,      // Timer for debouncing events
      debounceTimeout2: null,     // Second timer for observer events
      isMouseInside: false,       // Tracks if mouse is inside elements
      eventHandlers: new Map(),   // Stores event handlers for cleanup
      eventHandler: null,         // Main event handler reference
      originalStyle: new Map(),   // Stores original styles to restore after highlighting
      index: 0,                   // Current element index
      observer: null,             // MutationObserver reference
      container: '',              // CSS selector for container
      trackingElement: document.querySelector('body'), // Element to track mouse over
      showButtons: false,         // Whether debug buttons are shown
    }
  },

  async mounted() {
    // Initialize component and start polling for elements
    if (this.show) {
      console.log('%c PlotlyHighlighter buttons are visible', 'color: red; font-weight: bold; font-size: 12px')
    }
    console.log(`mounted PlotlyHighlighter for: ${this.viewer_id}`)
    this.container = `.${this.viewer_id} g.cartesianlayer > g > g.plot`
    this.showButtons = this.show
    
    // Poll for elements until found or timeout reached
    let checkDuration = 200 // 60 * 1000 // 60 seconds
    const interval = setInterval(() => {
      const els = this.queryElements()
      if (els.length > 0) {
        console.log(`there are ${els.length} elements`)
        clearInterval(interval)
        this.redo()
      }
      checkDuration -= 100
      if (checkDuration <= 0) {
        console.error('%c No elements found for PlotlyHighlighter', 'color: red; font-weight: bold; font-size: 18px')
        this.showButtons = this.debug
        clearInterval(interval)
      }
    }, 100);
    
  },

  methods: {
    // Find all histogram bar SVG paths
    queryElements() {
      return document.querySelectorAll(`${this.container} > g.barlayer2.mlayer > g > g > g > path`)
    },
    
    // Find a specific element by its data-index attribute
    queryElementByIndex(index) {
      return document.querySelector(`path[data-index='${index}']`)
    },
    
    /**
     * Find and process all histogram elements
     * Returns a promise that resolves when elements are found
     * Sets pointer-events to none and stores original styles
     */
    async getElements() {
      return new Promise((resolve, reject) => {
      let el = [];
      let found = false;
      
      const process = (element, index) => {
        element.style.pointerEvents = 'none';
        element.setAttribute('data-index', index);
        this.originalStyle.set(element, { style: element.style.cssText });
      };

      const interval = setInterval(() => {
        el = this.queryElements();
        if (el.length > 0) {
        console.log(`found ${el.length} elements`)
        found = true;
        this.el = el;
        clearInterval(interval);
        this.el.forEach(process);
        resolve(this.el);
        }
      }, 100);

      // Set a timeout to reject the promise if elements are not found within a certain time limit
      setTimeout(() => {
        clearInterval(interval);
        if (!found) {
        console.error('Elements not found within the time limit')
        reject(new Error('Elements not found within the time limit'));
        }
      }, 10000); // 10 seconds time limit
      });
    },
    
    // Verify all elements are still in the DOM
    checkElements() {
      for (element in this.el) {
        const index = element.dataset.index;
        if (index) {
          el = this.queryElementByIndex(index)
          if (el === null) {
            return false
          }
        }
      }
      return true
    },
    
    /**
     * Set up MutationObserver to watch for DOM changes
     * Automatically reapplies highlighting when Plotly graph updates
     */
    setupMutationObserver() {
      
      // this layer 
      let watchNode = document.querySelector(`${this.container} > g.barlayer2.mlayer`)
      
      if (watchNode === undefined || watchNode === null) {
        console.error('watch node is none')
        return
      }
      watchNode = watchNode.parentNode
      
      // Observer options
      const config = {attributes: true, childList: true, subtree: true}

      
      const callback = (mutationsList, observer) => {
        // Debounce the redo operation on mutation
        clearTimeout(this.debounceTimeout2);
        this.debounceTimeout2 = setTimeout(() => {
          for (let mutation of mutationsList) {
            // Check for path changes or node additions/removals
            if (
              (mutation.type === 'attributes' && mutation.attributeName === 'd') ||
              (mutation.type === 'childList' && 
              (mutation.addedNodes.length > 0 || mutation.removedNodes.length > 0))
            ) {
              observer.disconnect()
              this.observer = null
              this.redo();
              break;
            }
          }
        }, 50); // 50ms debounce
      }

      // Create an observer instance linked to the callback function
      this.observer = new MutationObserver(callback);
      this.observer.observe(watchNode, config);
    },
    
    // Apply highlight styles to an element
    highlightElement(element) {
      element.style.fill = this.fillColor
      element.style.fillOpacity = `${this.fillOpacity}`;
      element.style.stroke = this.strokeColor
      element.style.strokeOpacity = `${this.strokeOpacity}`;
      element.style.strokeWidth = `${this.strokeWidth}`;
      element.style.opacity = `${this.opacity}`;
    },
    
    // Remove highlighting and restore original styles
    unhighlightElement(element) {
      if (this.originalStyle.get(element)) {
        element.style.cssText = this.originalStyle.get(element).style;
      } else {
        element.style.fill = 'rgb(0,0,0)';
        element.style.fillOpacity = '0';
        element.style.stroke = 'rgb(0, 0, 0)';
        element.style.strokeOpacity = '0';
      }
    },
    
    /**
     * Set up mouse event listeners for highlighting
     * Uses requestAnimationFrame for performance
     * Determines which element to highlight based on mouse position
     */
    applyListeners() {      
      let currentlyHighlighted = null;
      let ticking = false;
      this.trackingElement = document.querySelector(`.${this.viewer_id}`)
      
      
      const trackMouse = (e) => {
        if (ticking) {
          return;
        }
        ticking = true;
        
        // Use requestAnimationFrame for smooth performance
        window.requestAnimationFrame(() => {
          let foundHighlighted = false;

          for (let element of this.el) {
            const rect = element.getBoundingClientRect();
            const isInside = (
              e.clientX > rect.left &&
              e.clientX < rect.right &&
              e.clientY >= rect.top &&
              e.clientY <= rect.bottom
            );
            
            if (isInside) {
              foundHighlighted = true;
              if (element !== currentlyHighlighted) {
                if (currentlyHighlighted !== null) {
                  this.unhighlightElement(currentlyHighlighted);
                }
                this.highlightElement(element);
                currentlyHighlighted = element;
              }
            }
          }
          
          if (!foundHighlighted && currentlyHighlighted !== null) {
            this.unhighlightElement(currentlyHighlighted);
            currentlyHighlighted = null;
          }
          if (!foundHighlighted) {
            currentlyHighlighted = null;
          }

          ticking = false;
        });
      }
      // Store handler for cleanup
      this.eventHandler = trackMouse;
      this.trackingElement.addEventListener('mousemove', trackMouse);

      this.setupMutationObserver();
    },

    // Remove event listeners for cleanup
    removeListeners() {
      if (this.eventHandler) {
        this.trackingElement.removeEventListener('mousemove', this.eventHandler);
        this.eventHandler = null;
      }
    },

    // Restart the highlighting process
    redo() {
      this.removeListeners()
      if (this.highlight) {
        this.getElements().then(() => {
          this.applyListeners()
        }).catch((error) => {
          console.error('Error:', error);
        });
      }
    },

  },
  
  // Clean up event listeners and observers when component is destroyed
  beforeDestroy() {
    this.removeListeners()
    if (this.observer !== null) {
      this.observer.disconnect()
    }
  },
  
  watch: {
    // Re-apply highlighting when props change
    highlight(value) {
      if (value) {
        this.redo()
      } else {
        this.removeListeners()
      }
    },
    
    show(value) {
      this.showButtons = value
    },
    
    viewer_id(value) {
      this.redo()
    }
    
  }
}

</script>

<template>
  <!-- For debugging only -->
  <v-col v-if="showButtons">
    Plotly Highlighting:
    <v-btn variant="outlined" @click="redo">Re-apply Highlighting</v-btn>
    <v-btn variant="outlined" @click="highlight = !highlight">Toggle Highlighting</v-btn>
  </v-col>
</template>
