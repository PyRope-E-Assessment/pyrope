define([
    'base/js/namespace',
    'base/js/events'
    ], function(Jupyter, events) {
		// Extract the autoexecute flag from metadata, hide and execute the
		// first cell if the flag was set to true.
		function autoexecute_first_cell() {
			var autoexecute = false;
			try {
				autoexecute = Jupyter.notebook.metadata.pyrope.autoexecute;
			} catch (e) {}
			if (autoexecute) {
				var cell = Jupyter.notebook.get_cell(0);
				cell.element.find('.input').hide();
				execute_first_cell();
			}
		}

		// Execute the first cell of a notebook. This only works if the
		// kernel for this notebook is already set. Otherwise an event is
		// defined which gets called when the kernel is ready.
		function execute_first_cell() {
			// use setTimeout to avoid error that model_ids for ipywidgets
			// are not found
			if (Jupyter.notebook.kernel) {
				setTimeout(function() {select_and_execute_cell(0)}, 2000);
			} else {
				events.one("kernel_ready.Kernel", (e) => {
					setTimeout(function() {select_and_execute_cell(0)}, 2000);
				});
			}
		}

		// Select a cell at a given index, execute it and select then
		// cell below.
		function select_and_execute_cell(cell_index) {
			Jupyter.notebook.select(cell_index);
			Jupyter.notebook.execute_cell_and_select_below();
		}

		return {
			load_ipython_extension: autoexecute_first_cell
		};
});


// Javascript functionalities for PyRope.
class PyRope {

	static widget_comms = {};

	// Creates a comm for a specific widget.
	static create_widget_comm(id) {
		this.widget_comms[id] = Jupyter.notebook.kernel.comm_manager.new_comm(id, {});
		Jupyter.notebook.kernel.comm_manager.register_target(
			id, function(comm, msg) {
				comm.on_msg(function(msg) {
				const widgets = document.querySelectorAll(`[data-pyrope-id="${id}"]`)
					let sync = false;
					if ("sync" in msg.metadata) {
						sync = msg.metadata.sync;
					}
					for (let i = 0; i < widgets.length; i++) {
						Object.keys(msg.content.data).forEach(function(key) {
							if (!sync || (sync && widgets[i] !== document.activeElement)) {
								widgets[i][key] = msg.content.data[key];
							}
						});
					}
				});
			}
		);
	}

	// display(Javascript(...)) creates an emtpy output_area with padding. To
	// avoid blank spaces between exercises this MutationObserver sets the
	// height of these output_areas to 0px.
	static observe_output_areas() {
		const observer = new MutationObserver(function(mutations) {
			mutations.forEach(function(mutation) {
				mutation.addedNodes.forEach(function(node) {
					if (node.className === "output_area") {
						const subarea = node.childNodes[2];
						if (subarea && subarea.classList.contains("output_javascript")) {
							// So that js error messages are still displayed.
							let js_error = false;
							subarea.childNodes.forEach(function(child) {
								if (child.classList.contains("js-error")) {
									js_error = true;
								}
							});
							if (!js_error) {
								node.style.height = "0px";
							}
						}
					}
				})
			})
		});

		observer.observe(
			document.getElementById("notebook"),
			{subtree: true, childList: true}
		);
	}

	// Send the information that a widget with data-pyrope-id 'id' has
	// currently the value 'value' to the python kernel via the designated
	// comm stored in 'widget_comms'.
	static send(id, value) {
		this.widget_comms[id].send({"value": value});
	}

	// This methods sets innerHTML for all nodes with data-pyrope-id 'pyrope_id' to
	// 'inner_html'. Note that 'inner_html' is a base64 encoded string.
	static set_inner_html(pyrope_id, inner_html) {
		document.querySelectorAll(`[data-pyrope-id="${pyrope_id}"]`).forEach(
			node => {
				node.innerHTML = new TextDecoder().decode(
					Uint8Array.from(atob(inner_html), (m) => m.codePointAt(0))
				);
				MathJax.Hub.Typeset(node);
			}
		);
	}

	// JupyterHtmlSlider can be rendered with a label displaying their
	// current value. This method updates the text content of labels
	// with data-pyrope-id 'label_id' to 'value'.
	static update_slider_label(label_id, value) {
		document.querySelectorAll(`[data-pyrope-id="${label_id}"]`).forEach(
			label => label.textContent = value
		);
	}

}

// Start observing when the extension is loaded.
PyRope.observe_output_areas();