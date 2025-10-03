# Tailwind CSS Setup

This project uses **Tailwind CSS v4** for styling, properly installed via npm (not CDN).

## Installation

Tailwind CSS v4 is already configured in this project. To set it up on a new machine:

```bash
# Install Node.js and npm (if not already installed)
sudo apt update && sudo apt install -y nodejs npm

# Install Tailwind CSS dependencies
npm install
```

## Development Workflow

### Building CSS for Production

To build the minified CSS file for production:

```bash
npm run build:css
```

This compiles `static/css/input.css` → `static/css/output.css` (minified).

### Development with Auto-Rebuild

To watch for changes and automatically rebuild CSS during development:

```bash
npm run watch:css
```

Leave this running in a separate terminal while making changes.

## File Structure

- **`package.json`** - Node.js dependencies and build scripts
- **`static/css/input.css`** - Source CSS file (Tailwind v4 with `@import` and `@theme`)
- **`static/css/output.css`** - Compiled/minified CSS (generated, not committed to git)
- **`templates/index_v3.html`** - HTML template that references the compiled CSS

## Tailwind v4 Configuration

Configuration is done in CSS (not JavaScript) using the `@theme` directive in `static/css/input.css`:

```css
@import "tailwindcss";

@theme {
  --color-primary: #2c3e50;
  --color-secondary: #3498db;
  --color-accent: #e74c3c;
  --color-success: #27ae60;
  --color-warning: #f39c12;
}
```

See `.cursor/rules/tailwindcss-rules.mdc` for full Tailwind v4 documentation.

## Why Not CDN?

The CDN version of Tailwind CSS is **not recommended for production** because:
- Much larger file size (includes entire framework)
- Slower performance (runtime CSS generation)
- No build optimization or tree-shaking
- Requires JavaScript to work

The proper npm installation provides:
- ✅ Minified, optimized CSS
- ✅ Only includes classes actually used
- ✅ No JavaScript required
- ✅ Better performance
- ✅ Production-ready

## Adding Custom Styles

Add custom styles to `static/css/input.css` and run `npm run build:css` to rebuild.

## Integration with Services

The `ledmatrix-web.service` should run `npm run build:css` during deployment to ensure the latest CSS is built.

