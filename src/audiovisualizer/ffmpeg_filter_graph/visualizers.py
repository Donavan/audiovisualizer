# FFmpeg Filter Graph Visualizers

from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class FilterGraphVisualizer:
    """Visualizes filter graphs for debugging."""
    
    @staticmethod
    def visualize(graph, output_path: Optional[str] = None) -> str:
        """Generate a visualization of the filter graph.
        
        This method generates a GraphViz DOT representation of the filter graph.
        If an output path is provided, it will attempt to save the visualization
        as an image file, assuming GraphViz is installed.
        
        Args:
            graph: The FilterGraph to visualize
            output_path: Optional path to save the visualization (requires graphviz)
            
        Returns:
            DOT representation of the graph as a string
        """
        dot = FilterGraphVisualizer._to_dot(graph)
        
        if output_path:
            try:
                # Try to use graphviz if available
                FilterGraphVisualizer._save_visualization(dot, output_path)
            except Exception as e:
                logger.warning(f"Could not save visualization: {e}")
                
        return dot
    
    @staticmethod
    def _to_dot(graph) -> str:
        """Convert a FilterGraph to GraphViz DOT format."""
        # Start the DOT file
        dot = "digraph FilterGraph {\n"
        dot += "  rankdir=LR;\n"
        dot += "  node [shape=box, style=filled, fillcolor=lightblue];\n\n"
        
        # Add nodes
        for node in graph.nodes:
            # Format label with filter type and parameters
            if node.params:
                params_str = "\n".join(f"{k}={v}" for k, v in node.params.items())
                label = f"{node.filter_type}\n{params_str}"
            else:
                label = node.filter_type
                
            dot += f"  \"{node.label}\" [label=\"{label}\"];\n"
        
        # Add edges
        for node in graph.nodes:
            for target, pad in node.outputs:
                dot += f"  \"{node.label}\" -> \"{target.label}\" [label=\"pad {pad}\"];\n"
        
        # Add external inputs
        for label, (node, pad) in graph.inputs.items():
            dot += f"  \"{label}\" [shape=ellipse, fillcolor=lightgreen];\n"
            dot += f"  \"{label}\" -> \"{node.label}\" [label=\"pad {pad}\"];\n"
        
        # Add external outputs
        for label, (node, pad) in graph.outputs.items():
            dot += f"  \"{label}_out\" [shape=ellipse, fillcolor=lightpink];\n"
            dot += f"  \"{node.label}\" -> \"{label}_out\" [label=\"pad {pad}\"];\n"
        
        dot += "}\n"
        return dot
    
    @staticmethod
    def _save_visualization(dot: str, output_path: str) -> None:
        """Save the DOT representation as an image file.
        
        This requires the graphviz package to be installed.
        
        Args:
            dot: DOT representation of the graph
            output_path: Path to save the visualization
        """
        try:
            import graphviz
            source = graphviz.Source(dot)
            source.render(output_path, format='png', cleanup=True)
            logger.info(f"Visualization saved to {output_path}.png")
        except ImportError:
            logger.warning("Graphviz package not found. Install with 'pip install graphviz' to save visualizations.")
            with open(f"{output_path}.dot", 'w') as f:
                f.write(dot)
            logger.info(f"DOT file saved to {output_path}.dot")