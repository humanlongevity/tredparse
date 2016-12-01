import React from 'react';

var Introduction = React.createClass({
  render: function () {

    var containerStyle = {
      fontFamily: '"Lato", sans-serif',
      padding: '0 0 30px 0',
      overflow: 'hidden'
    };

    var introductionHeaderStyle = {
      fontSize: '26px',
      lineHeight: '36px',
      fontWeight: '300',
      margin: '0 0 30px 0',
      textTransform: 'uppercase'
    };

    var buttonStyle = {
      fontWeight: 600,
      textTransform: 'uppercase',
      marginBottom: '50px'
    };

    return (
      <div className="container-fluid text-center">
        <div className="row">
          <div style={containerStyle}>

            <div className="col-sm-12">
              <h2 style={introductionHeaderStyle}>
                <strong> Short tandem repeats </strong> are a common source of
                genetic diseases that can be assayed through genome sequencing
              </h2>
              <a className="btn btn-success btn-lg" style={buttonStyle} href="https://github.com/tanghaibao/tredparse">
                  <i className="fa fa-github"></i> Find out how
              </a>
            </div>

          </div>
        </div>
      </div>
    );
  }
});

module.exports = Introduction;
