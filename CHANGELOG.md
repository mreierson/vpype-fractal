# Changelog

## 0.1.0

Initial release.

- L-system fractals: koch, sierpinski, dragon, hilbert, levy, gosper, peano, koch-island, minkowski, and custom lsystem with `--heading` support
- Escape-time fractals: mandelbrot, julia with contour extraction, smooth coloring, and viewport bounds validation
- Geometric fractals: tree (with `--branch-angle` and `--shrink` validation), carpet, sierpinski-triangle
- IFS fractals: ifs command with named presets (fern, maple, crystal, sierpinski-ifs), custom transforms, and weight validation
- Strange attractors: clifford, dejong, lorenz with named presets and full parameter control
- Optional pen set integration via vpype-penset for multi-pen plotter output
- Vectorized marching squares contour extraction with proper saddle point disambiguation
- Vectorized escape-time iteration loop with single `np.abs(z)` computation per iteration
- L-system expansion safety limit to prevent out-of-memory on exponential growth
- Five core engines with clean separation from CLI commands
