# FFmpeg Filter Graph Converters

from typing import List, Set, Dict


class FilterGraphConverter:
    """Converts FilterGraph to FFmpeg filter chain syntax."""

    @staticmethod
    def to_string(graph) -> str:
        """Convert a FilterGraph to an FFmpeg filter chain string.
        
        Args:
            graph: The FilterGraph to convert
            
        Returns:
            String representation of the filter graph in FFmpeg syntax
        """
        # Process nodes in topological order
        sorted_nodes = FilterGraphConverter._topological_sort(graph)

        # Generate filter strings for each node
        result = []
        for node in sorted_nodes:
            # Generate the filter string with proper input/output labels
            filter_str = FilterGraphConverter._node_to_string(node, graph)
            if filter_str:
                result.append(filter_str)

        return ";".join(result)

    @staticmethod
    def _node_to_string(node, graph) -> str:
        """Convert a single node to a filter string with proper labels."""
        # Input labels
        input_labels = []

        for i, (source, _) in enumerate(node.inputs):
            label = node.get_input_label(i)
            if label:
                input_labels.append(f"[{label}]")

        # Output labels
        output_labels = []
        # Check if this node's outputs are used as graph outputs
        output_found = False

        for label, (out_node, pad) in graph.outputs.items():
            if out_node == node:
                output_labels.append(f"[{label}]")
                output_found = True
                continue

        # If not a graph output and has connected outputs, use the node's output label
        if not output_found and node.outputs:
            label = node.get_output_label()
            output_labels.append(f"[{label}]")

        # Special case: if it's a terminal node with no outputs and not marked as a graph output
        elif not output_found and not node.outputs:
            # Get the sorted nodes to check if this is the last node
            sorted_nodes = list(graph.nodes)  # Use all nodes as fallback

            # If this is the last node and there are no defined outputs, make it the default output
            if not graph.outputs and node == sorted_nodes[-1]:
                output_labels.append("[out]")

        # Combine into a complete filter string
        if input_labels or output_labels:
            return f"{''.join(input_labels)}{node.to_filter_string()}{''.join(output_labels)}"

        return ""

    @staticmethod
    def _topological_sort(graph) -> List:

        """Sort nodes in topological order (inputs before outputs)."""

        visited = set()

        temp_mark = set()

        order = []

        def visit(node):

            if node in temp_mark:
                raise ValueError("Graph contains a cycle")

            if node in visited:
                return

            temp_mark.add(node)

            # Process all outputs of this node

            for target, _ in node.outputs:
                visit(target)

            temp_mark.remove(node)

            visited.add(node)

            order.append(node)

        # Start with nodes that have no inputs or are connected to external inputs

        source_nodes = []

        for node in graph.nodes:

            if not node.inputs or any(node == input_node for input_node, _ in graph.inputs.values()):
                source_nodes.append(node)

        # Process source nodes first

        for node in source_nodes:

            if node not in visited:
                visit(node)

        # Process any remaining nodes - this is important for disconnected subgraphs

        for node in graph.nodes:

            if node not in visited:
                visit(node)

        # Return in reverse order (dependencies first)

        return list(reversed(order))


class FilterGraphParser:
    """Parses FFmpeg filter strings into a FilterGraph."""

    @staticmethod
    def parse_filter_chains(filter_chains: List[str]):
        """Parse a list of filter chain strings into a FilterGraph.
        
        This is primarily for backward compatibility with the old API.
        
        Args:
            filter_chains: List of filter chain strings in FFmpeg syntax
            
        Returns:
            A FilterGraph representing the parsed chains
        """
        from .core import FilterGraph
        
        graph = FilterGraph()
        
        # Simple parsing of filter chains
        # This is a limited implementation for backward compatibility
        # Full parsing would be more complex
        
        for chain in filter_chains:
            # Parse the chain and create nodes
            # For now, we just create a single node with the entire chain as a parameter
            # This is a placeholder - a full implementation would parse the chain properly
            graph.create_node('complex', params={'filter_complex': chain})
        
        return graph