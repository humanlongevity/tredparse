import React from 'react';

const PageModal = React.createClass({
  propTypes: {
    text: React.PropTypes.string.isRequired,
    link: React.PropTypes.string.isRequired,
  },

  getInitialState() {
    return { show: false };
  },

  open() {
    this.setState({ show: true });
  },

  close() {
    this.setState({ show: false });
  },

  render() {
    return (
      <div>
        <a href={ this.props.link }
          title={ this.props.text }
          data-toggle='modal'
          data-target='#largeModal'
          target='_blank'
          onClick={ this.open }
        >
          { this.props.text }
        </a>
      </div>
    );
  },
});

module.exports = PageModal;
