import React from 'react';
import { Col, Row } from 'react-bootstrap';

const Footer = React.createClass({
  render() {
    const containerStyle = {
      fontFamily: '"Lato", sans-serif',
      padding: '40px 0',
      borderTop: '1px solid #ddd',
      overflow: 'hidden',
      color: '#ccc',
    };

    const footerContentStyle = {
      fontSize: '16px',
      fontWeight: '200',
      margin: 0,
    };

    return (
      <div className="container-fluid text-center">
        <Row>
          <div style={containerStyle} data-style-footer>
            <Col sm={ 12 }>
              <p style={footerContentStyle}>
                Built by <a href="http://github.com/tanghaibao">Haibao Tang</a> in 2016
              </p>
            </Col>
          </div>
        </Row>
      </div>
    );
  },
});

module.exports = Footer;
