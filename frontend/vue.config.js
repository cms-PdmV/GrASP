const isProd = process.env.NODE_ENV === "production"

module.exports = {
  "transpileDependencies": [
    "vuetify"
  ],
  publicPath: isProd ? '/grasp' : '',
  assetsDir: 'static/',
  devServer: {
    port: 8003,
    logLevel: 'debug'
  }
}
