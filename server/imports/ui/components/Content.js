import React from 'react';
import { Col, Row } from 'react-bootstrap';
import FormInput from './FormInput';
import FormOutput from './FormOutput';

const Content = React.createClass({
  getInitialState() {
    return {
      bam: null,
      tred: null,
    };
  },

  handleClick(t) {
    this.setState({ tred: t });
  },

  render() {
    const containerStyle = {
      fontFamily: '"Lato", sans-serif',
      padding: '30px 0',
      borderTop: '1px solid #ddd',
      overflow: 'hidden',
    };

    const contentHeaderStyle = {
      fontSize: '26px',
      lineHeight: '36px',
      fontWeight: '300',
      margin: '0 0 30px 0',
      textTransform: 'uppercase',
    };

    const contentStyle = {
      fontSize: '20px',
    };

    return (
      <div className="container-fluid text-center">
        <Row>
          <div style={containerStyle}>
            <Col sm={ 12 }>
              <h3 style={contentHeaderStyle}>Interactive demo</h3>
              <p style={contentStyle}>
                Our STR caller requires <strong>BAM</strong> file as well as <strong>STR locus</strong>
              </p>
              <p></p>
              <FormInput clickHandler={ this.handleClick } />
              <p></p>
              <FormOutput object={ this.state.tred } />
            </Col>
          </div>
        </Row>
      </div>
    );
  },
});

module.exports = Content;
