<script>
export default {

  data() {
    return {
      el: []
    }
  },

  async mounted() {
    this.getElements()
    this.applyListeners()
  },

  methods: {
    getElements() {
      this.el = document.querySelectorAll('g.cartesianlayer > g > g.plot > g.barlayer2.mlayer > g > g > g > path')
      console.log(this.el)
    },

    applyListeners() {
      console.log('apply listeners')
      this.el.forEach(element => {
        // Enable pointer events for this element and its ancestors
        // enablePointerEvents(element);
        // element.style.pointerEvents = 'auto';
        // console.log(element)

        let i = 0
        // Add mouseover event listener
        let isMouseInside = false;
        let debounceTimeout;

        // Add mouseenter event listener
        element.addEventListener('mouseenter', function () {
          if (!isMouseInside) {
            isMouseInside = true;
            console.log('entered');
            element.style.fill = 'rgb(0, 0, 0)';
            element.style.fillOpacity = '0.5';
            element.style.stroke = 'rgb(120, 120, 255)';
            element.style.strokeOpacity = '1';
          }
        });

        // Add mouseleave event listener
        element.addEventListener('mouseleave', function () {
          if (isMouseInside) {
            clearTimeout(debounceTimeout);
            debounceTimeout = setTimeout(() => {
              isMouseInside = false;
              console.log('leave');
              element.style.fill = 'none'; // Revert to initial styles
              element.style.fillOpacity = '0';
              element.style.stroke = 'none';
              element.style.strokeOpacity = '0';
            }, 100); // Adjust the debounce time as needed
          }
        });

        // Apply styles

      });
    },

    redo() {
      this.getElements()
      this.applyListeners()
    }
  }
}

</script>

<template>
  <v-col>
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