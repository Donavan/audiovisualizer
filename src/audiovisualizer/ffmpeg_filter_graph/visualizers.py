# FFmpeg Filter Graph Visualizers

from typing import Optional, Dict, Any, List, Union
import logging
from pathlib import Path
import json
import os

logger = logging.getLogger(__name__)


class FilterGraphVisualizer:
    """Visualizes filter graphs for debugging and documentation purposes.
    
    This class provides methods to generate visual representations of FFmpeg filter
    graphs using GraphViz. It supports multiple output formats and styling options.
    """
    
    # Default node styling for different node types
    DEFAULT_STYLES = {
        'node': {
            'shape': 'box',
            'style': 'filled',
            'fillcolor': 'lightblue',
            'fontname': 'Arial',
            'margin': '0.2,0.1'
        },
        'input': {
            'shape': 'ellipse',
            'fillcolor': 'lightgreen',
            'fontname': 'Arial',
            'style': 'filled'
        },
        'output': {
            'shape': 'ellipse',
            'fillcolor': 'lightpink',
            'fontname': 'Arial',
            'style': 'filled'
        },
        'edge': {
            'fontname': 'Arial',
            'fontsize': '10',
            'fontcolor': 'darkblue'
        }
    }
    
    @staticmethod
    def visualize(graph, output_path: Optional[str] = None, 
                 format: str = 'png', styles: Optional[Dict] = None,
                 open_file: bool = False) -> str:
        """Generate a visualization of the filter graph.
        
        This method generates a GraphViz DOT representation of the filter graph.
        If an output path is provided, it will attempt to save the visualization
        as an image file, assuming GraphViz is installed.
        
        Args:
            graph: The FilterGraph to visualize
            output_path: Optional path to save the visualization (requires graphviz)
            format: Output format ('png', 'svg', 'pdf', etc.)
            styles: Optional custom styling for nodes and edges
            open_file: If True, attempt to open the generated file
            
        Returns:
            DOT representation of the graph as a string
        """
        # Merge default styles with any custom styles
        merged_styles = FilterGraphVisualizer._merge_styles(
            FilterGraphVisualizer.DEFAULT_STYLES,
            styles or {}
        )
        
        # Generate DOT format with the merged styles
        dot = FilterGraphVisualizer._to_dot(graph, merged_styles)
        
        if output_path:
            try:
                # Try to use graphviz if available
                output_file = FilterGraphVisualizer._save_visualization(
                    dot, output_path, format)
                
                # Open the file if requested
                if open_file and output_file:
                    FilterGraphVisualizer._open_file(output_file)
                    
            except Exception as e:
                logger.warning(f"Could not save visualization: {e}")
                # Save the DOT file as a fallback
                dot_path = f"{output_path}.dot"
                with open(dot_path, 'w') as f:
                    f.write(dot)
                logger.info(f"DOT file saved to {dot_path}")
                
        return dot
    
    @staticmethod
    def _merge_styles(default_styles: Dict, custom_styles: Dict) -> Dict:
        """Merge default styles with custom styles."""
        merged = {}
        for key in set(default_styles.keys()) | set(custom_styles.keys()):
            if key in default_styles and key in custom_styles:
                merged[key] = {**default_styles[key], **custom_styles[key]}
            elif key in default_styles:
                merged[key] = default_styles[key]
            else:
                merged[key] = custom_styles[key]
        return merged
    
    @staticmethod
    def _to_dot(graph, styles: Dict) -> str:
        """Convert a FilterGraph to GraphViz DOT format with styling."""
        # Start the DOT file
        dot = "digraph FilterGraph {\n"
        dot += "  rankdir=LR;\n"
        
        # Add default node and edge styling
        node_style = " ".join(f"{k}={v}" for k, v in styles['node'].items())
        edge_style = " ".join(f"{k}={v}" for k, v in styles['edge'].items())
        dot += f"  node [{node_style}];\n"
        dot += f"  edge [{edge_style}];\n\n"
        
        # Add nodes with their properties
        for node in graph.nodes:
            # Format label with filter type and parameters
            if node.params:
                params_list = []
                for k, v in node.params.items():
                    # Format the value based on its type
                    if isinstance(v, str) and len(v) > 20:
                        v_str = f"{v[:17]}..."
                    else:
                        v_str = str(v)
                    params_list.append(f"{k}={v_str}")
                
                params_str = "\\n".join(params_list)
                label = f"{node.filter_type}\\n{params_str}"
            else:
                label = node.filter_type
            
            # Add the node with its label
            dot += f"  \"{node.label}\" [label=\"{label}\"];\n"
        
        # Add edges between nodes
        for node in graph.nodes:
            for target, pad in node.outputs:
                # Find the corresponding input pad on the target node
                target_pad = next((i for i, (src, _) in enumerate(target.inputs) 
                                  if src == node), 0)
                
                edge_label = f"out:{pad} → in:{target_pad}"
                dot += f"  \"{node.label}\" -> \"{target.label}\" [label=\"{edge_label}\"];\n"
        
        # Add external inputs with special styling
        input_style = " ".join(f"{k}={v}" for k, v in styles['input'].items())
        for label, (node, pad) in graph.inputs.items():
            dot += f"  \"{label}\" [{input_style}, label=\"Input\\n{label}\"];\n"
            dot += f"  \"{label}\" -> \"{node.label}\" [label=\"→ pad {pad}\"];\n"
        
        # Add external outputs with special styling
        output_style = " ".join(f"{k}={v}" for k, v in styles['output'].items())
        for label, (node, pad) in graph.outputs.items():
            output_id = f"{label}_out"
            dot += f"  \"{output_id}\" [{output_style}, label=\"Output\\n{label}\"];\n"
            dot += f"  \"{node.label}\" -> \"{output_id}\" [label=\"pad {pad} →\"];\n"
        
        dot += "}\n"
        return dot
    
    @staticmethod
    def _save_visualization(dot: str, output_path: str, format: str = 'png') -> Optional[str]:
        """Save the DOT representation as an image file.
        
        This requires the graphviz package to be installed.
        
        Args:
            dot: DOT representation of the graph
            output_path: Path to save the visualization
            format: Output format (png, svg, pdf, etc.)
            
        Returns:
            Path to the generated file or None if generation failed
        """
        try:
            import graphviz
            source = graphviz.Source(dot)
            
            # Ensure the directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Render with the specified format
            result = source.render(filename=output_path, format=format, cleanup=True)
            logger.info(f"Visualization saved to {result}")
            return result
            
        except ImportError:
            logger.warning("Graphviz package not found. Install with 'pip install graphviz' to save visualizations.")
            dot_path = f"{output_path}.dot"
            with open(dot_path, 'w') as f:
                f.write(dot)
            logger.info(f"DOT file saved to {dot_path}")
            return dot_path
        except Exception as e:
            logger.error(f"Error saving visualization: {str(e)}")
            return None
    
    @staticmethod
    def _open_file(file_path: str) -> None:
        """Attempt to open the generated file with the default application."""
        try:
            import os
            import platform
            import subprocess
            
            system = platform.system()
            if system == 'Darwin':  # macOS
                subprocess.run(['open', file_path], check=True)
            elif system == 'Windows':
                os.startfile(file_path)
            else:  # Linux
                subprocess.run(['xdg-open', file_path], check=True)
                
            logger.info(f"Opened file: {file_path}")
        except Exception as e:
            logger.warning(f"Could not open file: {str(e)}")
    
    @staticmethod
    def generate_html_preview(graph, include_styles: bool = True) -> str:
        """Generate an HTML preview of the graph using SVG.
        
        This is useful for displaying the graph in notebooks or web interfaces.
        
        Args:
            graph: The FilterGraph to visualize
            include_styles: Whether to include CSS styles
            
        Returns:
            HTML string containing the SVG visualization
        """
        try:
            import graphviz
            import tempfile
            
            # Generate the DOT representation
            dot = FilterGraphVisualizer._to_dot(graph, FilterGraphVisualizer.DEFAULT_STYLES)
            
            # Use graphviz to create an SVG
            source = graphviz.Source(dot)
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as tmp:
                temp_path = tmp.name
            
            # Render to SVG
            source.render(filename=temp_path, format='svg', cleanup=True)
            svg_path = f"{temp_path}.svg"
            
            # Read the SVG content
            with open(svg_path, 'r') as f:
                svg_content = f.read()
            
            # Clean up temporary files
            try:
                os.remove(svg_path)
                os.remove(temp_path)
            except:
                pass
                
            # Simple HTML wrapper for the SVG
            html = "<div class='filter-graph-visualization'>"
            
            # Add CSS styles if requested
            if include_styles:
                html += """
                <style>
                .filter-graph-visualization {
                    max-width: 100%;
                    overflow: auto;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 10px;
                    background-color: white;
                }
                .filter-graph-visualization svg {
                    display: block;
                    margin: 0 auto;
                }
                </style>
                """
                
            # Add the SVG content
            html += svg_content
            html += "</div>"
            
            return html
            
        except Exception as e:
            logger.error(f"Error generating HTML preview: {str(e)}")
            return f"<div><p>Error generating visualization: {str(e)}</p></div>"


class JSONVisualizer:
    """Converts filter graphs to JSON format for custom visualization."""
    
    @staticmethod
    def to_json(graph) -> str:
        """Convert a FilterGraph to JSON format.
        
        This is useful for creating custom visualizations or for serializing
        the graph structure for external tools.
        
        Args:
            graph: The FilterGraph to convert
            
        Returns:
            JSON string representation of the graph
        """
        data = {
            "nodes": [],
            "edges": [],
            "inputs": [],
            "outputs": []
        }
        
        # Add nodes
        node_index_map = {}  # Maps nodes to their index for edge creation
        for i, node in enumerate(graph.nodes):
            node_index_map[node] = i
            node_data = {
                "id": i,
                "label": node.label,
                "filter_type": node.filter_type,
                "params": node.params
            }
            data["nodes"].append(node_data)
        
        # Add edges
        edge_id = 0
        for source_node in graph.nodes:
            source_id = node_index_map[source_node]
            for target_node, source_pad in source_node.outputs:
                # Find the target pad
                target_id = node_index_map[target_node]
                target_pad = next((i for i, (src, _) in enumerate(target_node.inputs) 
                                if src == source_node), 0)
                
                edge_data = {
                    "id": edge_id,
                    "source": source_id,
                    "target": target_id,
                    "source_pad": source_pad,
                    "target_pad": target_pad
                }
                data["edges"].append(edge_data)
                edge_id += 1
        
        # Add external inputs
        for label, (node, pad) in graph.inputs.items():
            input_data = {
                "label": label,
                "node": node_index_map[node],
                "pad": pad
            }
            data["inputs"].append(input_data)
        
        # Add external outputs
        for label, (node, pad) in graph.outputs.items():
            output_data = {
                "label": label,
                "node": node_index_map[node],
                "pad": pad
            }
            data["outputs"].append(output_data)
        
        return json.dumps(data, indent=2)
    
    @staticmethod
    def save_json(graph, output_path: str) -> None:
        """Save the graph as a JSON file.
        
        Args:
            graph: The FilterGraph to save
            output_path: Path to save the JSON file
        """
        json_data = JSONVisualizer.to_json(graph)
        
        # Ensure the directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        with open(output_path, 'w') as f:
            f.write(json_data)
        
        logger.info(f"JSON representation saved to {output_path}")