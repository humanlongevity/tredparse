var React = require('react');

var Brand = React.createClass({
  render: function () {

    return (
      <div>
        <a href="http://www.humanlongevity.com" class="logo">
          <img src="/static/logo.png" alt="Human Longevity, Inc." class="tt-retina-logo" />
        </a>
      </div>
    );
  }
});

module.exports = Brand;
