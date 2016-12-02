import React from 'react';
import Brand from './Brand';
import { Col, Row } from 'react-bootstrap';

const Header = React.createClass({
  render() {
    const containerStyle = {
      fontFamily: '"Lato", sans-serif',
      margin: '40px 0',
      overflow: 'hidden',
    };

    return (
      <div className="container-fluid">
        <Row>
          <div style={containerStyle}>
            <Col sm={ 5 }>
              <Brand />
            </Col>
            <Col sm={ 7 }>
            </Col>
          </div>
        </Row>
      </div>
    );
  },
});

module.exports = Header;
