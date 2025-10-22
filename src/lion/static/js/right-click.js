// Create the main div element
export function create_menu(){
    
    let contextMenuDiv = document.createElement('div');
    contextMenuDiv.id = 'contextMenu';
    contextMenuDiv.style.display = 'none';
    contextMenuDiv.style.position = 'absolute';
    contextMenuDiv.style.backgroundColor = '#ffffff';
    contextMenuDiv.style.border = 'solid 1px #000000';
    contextMenuDiv.style.zIndex = '50';
    
    // Create the ul element
    let ulElement = document.createElement('ul');
    
    // Create the first li element
    let li1 = document.createElement('li');
    li1.id = 'menuOption1';
    li1.textContent = 'Option 1';
    
    // Create the second li element
    let li2 = document.createElement('li');
    li2.id = 'menuOption2';
    li2.textContent = 'Option 2';
    
    // Append the li elements to the ul
    ulElement.appendChild(li1);
    ulElement.appendChild(li2);
    
    // Append the ul to the div
    contextMenuDiv.appendChild(ulElement);
    
    // Append the div to the body
    document.body.appendChild(contextMenuDiv);    
}
