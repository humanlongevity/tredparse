import React from 'react';
import { Row, Col } from 'react-bootstrap';
import classNames from 'classnames';

const Frame = React.createClass({
  propTypes: {
    src: React.PropTypes.string.isRequired,
    onLoad: React.PropTypes.func,
  },

  componentDidMount() {
    this.refs.iframe.addEventListener('load', this.props.onLoad);
  },

  render() {
    return <iframe ref="iframe" {...this.props}/>;
  },
});

const IFrame = React.createClass({
  propTypes: {
    url: React.PropTypes.string.isRequired,
  },

  getInitialState() {
    return {
      isLoading: true,
    };
  },

  render() {
    const classes = classNames({
      'is-loading': this.state.isLoading,
    });

    return (
        <div>
          { this.state.isLoading ?
            <p>Loading... A spinner would probably be nice here</p>
            : null
          }
          <Row>
            <Col sm={ 12 }>
              <Frame
                className={ classes }
                frameBorder={ 0 }
                style={{ width: '100%', height: 600 }}
                onLoad={ this.iframeLoaded }
                src={ this.props.url }
              />
            </Col>
          </Row>
        </div>
    );
  },

  iframeLoaded() {
    this.setState({
      isLoading: false,
    });
  },
});

module.exports = IFrame;
