var React = require('react');

var Navigation = React.createClass({
  render: function () {

    var navigationStyle = {
      margin: '25px 0',
      textTransform: 'uppercase',
      textAlign: 'center'
    };

    var navigationIteamStyle = {
      display: 'inline-block',
      width: '100px',
      margin: '0 20px',
      fontSize: '16px',
      fontWeight: '400',
      color: '#000000',
      textTransform: 'uppercase',
      lineHeight: '30px'
    };

    return (
      <div style={navigationStyle}>
        <div className="row">
          <div className="col-sm-8 col-sm-offset-1">
            <div className="row">
              <div className="col-sm-5">
                <span style={navigationIteamStyle}>Item 1</span>
              </div>
              <div className="col-sm-4">
                <span style={navigationIteamStyle}>Item 2</span>
              </div>
              <div className="col-sm-3">
                <span style={navigationIteamStyle}>Item 3</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }
});

module.exports = Navigation;
