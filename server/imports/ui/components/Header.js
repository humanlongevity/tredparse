import React from 'react';
import Brand from './Brand';

const Header = React.createClass({
  render: () => {
    const containerStyle = {
      fontFamily: '"Lato", sans-serif',
      margin: '40px 0',
      overflow: 'hidden',
    };

    return (
      <div className="container-fluid">
        <div className="row">
          <div style={containerStyle}>
            <div className="col-sm-5">
              <Brand />
            </div>
            <div className="col-sm-7">
            </div>
          </div>
        </div>
      </div>
    );
  },
});

module.exports = Header;
