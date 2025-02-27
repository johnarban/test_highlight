<script>
export default {

  data() {
    return {
      el: [],
      hoverDuration: 0,
      debounceTimeout: null,
      isMouseInside: false,
      // create a map to store the eventhandler for removal
      eventHandlers: new Map(),
      originalStyle: new Map()
      
    }
  },

  async mounted() {
    this.getElements()
    this.applyListeners()
  },

  methods: {
    getElements() {
      this.el = document.querySelectorAll('g.cartesianlayer > g > g.plot > g.barlayer2.mlayer > g > g > g > path')
      console.log(`Got ${this.el.length} elements`)
      this.el.forEach((element, index) => {
        element.style.pointerEvents = 'auto';
        element.setAttribute('data-index', index);
        this.originalStyle.set(element, {style: element.style.cssText} );
      });
    },
    
    applyListeners() {
      console.log('apply listeners')
      this.el.forEach(element => {
        let isMouseInside = false;
        let debounceTimeout;
        let hoverDuration = 0;

        // Add mouseenter event listener
        const enterHandler = () => {
          if (!isMouseInside) {
            hoverDuration = performance.now();
            isMouseInside = true;
            element.style.fill = 'rgb(0, 0, 0)';
            element.style.fillOpacity = '0.5';
            element.style.stroke = 'rgb(120, 120, 255)';
            element.style.strokeOpacity = '1';
          }
        }
        
        this.eventHandlers.set(element, { enterHandler });
        element.addEventListener('mouseenter', enterHandler);

        // Add mouseleave event listener
        const leaveHandler = () => {
          if (isMouseInside) {
            const diff = performance.now() - hoverDuration;
            const debounceTime = diff > 500 ? 100 : 0;
            clearTimeout(debounceTimeout);
            debounceTimeout = setTimeout(() => {
              isMouseInside = false;
              if (this.originalStyle.get(element) === undefined) {
                element.style.fill = 'rgb(0,0,0)';
                element.style.fillOpacity = '0';
                element.style.stroke = 'rgb(0, 0, 0)';
                element.style.strokeOpacity = '0';
              }
              element.style.cssText = this.originalStyle.get(element).style;
            }, debounceTime); // Adjust the debounce time as needed
          }
        }
        
        this.eventHandlers.set(element, { leaveHandler });
        element.addEventListener('mouseleave', leaveHandler );

      });
      
    },
    
    removeListeners() {
      this.el.forEach(element => {
        if (this.eventHandlers.size === 0) return;
        enterHandler = this.eventHandlers.get(element).enterHandler;
        leaveHandler = this.eventHandlers.get(element).leaveHandler;
        element.removeEventListener('mouseenter', enterHandler);
        element.removeEventListener('mouseleave', leaveHandler);
      });
    },

    redo() {
      this.removeListeners()
      this.getElements()
      this.applyListeners()
    }
  }
}

</script>

<template>
  <v-col>
    Plotly Highlighting
    <v-btn variant="outlined" @click="redo">Redo</v-btn>
  </v-col>
</template>

<style>
button.ph-redo
{
  background-color: white;
  padding: 0.5em 1em;
  border-radius: 5px;
  filter: drop-shadow(0 0px 5px black);

  box-shadow: 0 0 0 black;
  width: fit-content;
}
</style>