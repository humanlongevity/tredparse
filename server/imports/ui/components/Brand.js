import React from 'react';

var Brand = React.createClass({
  render: function () {

    return (
      <div>
        <a href="http://www.humanlongevity.com" className="logo">
          <img src="/logo.png" alt="Human Longevity, Inc." className="tt-retina-logo" />
        </a>
      </div>
    );
  }
});

module.exports = Brand;
