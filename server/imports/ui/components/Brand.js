import React from 'react';

const Brand = React.createClass({
  render: () => {
    return (
      <div>
        <a href="http://www.humanlongevity.com" className="logo">
          <img src="/logo.png" alt="Human Longevity, Inc." className="tt-retina-logo" />
        </a>
      </div>
    );
  },
});

module.exports = Brand;
