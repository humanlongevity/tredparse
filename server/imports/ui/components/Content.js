import React from 'react';
import Brand from './Brand';
import Navigation from './Navigation';
import RunForm from './RunForm';

var Content = React.createClass({
  render: function () {

    var containerStyle = {
      fontFamily: '"Lato", sans-serif',
      padding: '30px 0',
      borderTop: '1px solid #ddd',
      overflow: 'hidden'
    };

    var contentHeaderStyle = {
      fontSize: '26px',
      lineHeight: '36px',
      fontWeight: '300',
      margin: '0 0 30px 0',
      textTransform: 'uppercase'
    };

    var contentStyle = {
      fontSize: '20px',
      margin: 0
    };

    return (
      <div className="container-fluid text-center">
        <div className="row">
          <div style={containerStyle}>

            <div className="col-sm-12">
              <h3 style={contentHeaderStyle}>Interactive demo</h3>
              <p style={contentStyle}>
                Our STR caller requires a BAM file as well as the STR locus
              </p>
              <p></p>
              <RunForm />
            </div>

          </div>
        </div>
      </div>
    );
  }
});

module.exports = Content;
