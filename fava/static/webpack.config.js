var webpack = require('webpack');
var path = require('path');
var ExtractTextPlugin = require('extract-text-webpack-plugin');

var extractThemeDefaultCSS     = new ExtractTextPlugin('theme_default.css',     { allChunks: true });
var extractThemeAlternativeCSS = new ExtractTextPlugin('theme_alternative.css', { allChunks: true });

module.exports = {
  entry: {
    'app': './javascript/main.js',
    'editor': './javascript/editor.js',
    'theme_default': './sass/theme_default.scss',
    'theme_alternative': './sass/theme_alternative.scss'
  },
  output: {
    path: __dirname + '/gen',
    filename: '[name].js'
  },
  module: {
    loaders: [
      {
        test: /theme_default\.scss$/,
        loader: extractThemeDefaultCSS.extract('style-loader', 'css-loader!sass-loader')
      },
      {
        test: /theme_alternative\.scss$/,
        loader: extractThemeAlternativeCSS.extract('style-loader', 'css-loader!sass-loader')
      },
      {
        test: [/ace-builds.*/, /.*ace-mode-beancount.*/],
        loader: 'script-loader'
      },
      {
        test   : /\.(ttf|eot|svg|woff(2)?)(\?[a-z0-9]+)?$/,
        loader : 'file-loader'
      }
    ]
  },
  plugins: [
    new webpack.optimize.UglifyJsPlugin(),
    new webpack.ProvidePlugin({
      $: 'jquery',
      jQuery: 'jquery',
    }),
    extractThemeDefaultCSS,
    extractThemeAlternativeCSS
  ],
}
