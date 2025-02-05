el = document.querySelectorAll('g.cartesianlayer > g > g.plot > g.barlayer2.mlayer > g > g > g > path')

function enablePointerEvents(element) {
    // Ensure the element itself accepts pointer events
    // element.style.pointerEvents = 'auto';
    
    // Traverse up the DOM tree
    let currentElement = element.parentElement;
    while (currentElement) {
        // Prevent parent elements from blocking pointer events
        currentElement.style.pointerEvents = 'auto';
        currentElement = currentElement.parentElement;
    }
}

el.forEach(element => {
    // Enable pointer events for this element and its ancestors
    // enablePointerEvents(element);
    element.style.pointerEvents = 'auto';
    
    element.style['fill'] = 'rgba(158, 39, 39, 0.37)';
    element.style['fill-opacity'] = 0.5;
    
    // Add mouseover event listener
    element.addEventListener('mouseenter', e => {
        e.stopPropagation()
        console.log('mouseenter', e)
        element.style['fill'] = 'rgb(0, 0, 0)';
        element.style['fill-opacity'] = 0.5;
        element.style['stroke'] = 'rgb(120, 120, 255)';
        element.style['stroke-opacity'] = '1';
    });
    element.addEventListener('mouseleave', e => {
        e.stopPropagation()
        console.log('mouseleave')
        element.style['fill'] = 'rgb(0,0,0)';
        element.style['fill-opacity'] = 0;
        element.style['stroke'] = 'rgb(0,0,0)';
        element.style['stroke-opacity'] = '1';
    });
    
    // Apply styles
    
});