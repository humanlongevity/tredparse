import React from 'react';
import { Button, Modal } from 'react-bootstrap';

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

        <Modal
          id='largeModal'
          show={ this.state.show }
          onHide={ this.close }
          dialogClassName='custom-modal'
        >
          <Modal.Header closeButton>
            <Modal.Title>Title</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            Body
          </Modal.Body>
          <Modal.Footer>
            <Button onClick={ this.close }>Close</Button>
          </Modal.Footer>
        </Modal>
      </div>
    );
  },
});

module.exports = PageModal;