function hideFunction(nodeId) {
   var ul = document.getElementById(nodeId)
   ul.className = (ul.className=="nodeOpenClass") ? "nodeCloseClass" : "nodeOpenClass"
}
