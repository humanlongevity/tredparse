import React from 'react';
import { ReactMeteorData } from 'meteor/react-meteor-data';
import { Meteor } from 'meteor/meteor';
import { Col, Row } from 'react-bootstrap';
import Documents from '../../api/documents/documents';
import FormInput from './FormInput';
import FormOutput from './FormOutput';
import Default from './Default';
import Loading from './Loading';

const Content = React.createClass({
  getInitialState() {
    return {
      currentTitle: '',
      bam: Default.s3BAM,
      tred: Default.tred,
    };
  },

  mixins: [ReactMeteorData],
  getMeteorData() {
    let data = {};
    const currentTitle = this.state.currentTitle;
    const handle = Meteor.subscribe('documents.viewtitle', currentTitle);
    if (handle.ready()) {
      data.post = Documents.findOne({ title: currentTitle });
    }
    return data;
  },

  handleClick(tred) {
    this.setState({ tred });
  },

  handleSubmit(bam) {
    const cmd = `docker run --rm tanghaibao/tredparse tred.py ${bam} --tred ${this.state.tred} --log DEBUG`;
    const currentTitle = cmd;
    Meteor.call('shell', { cmd },
      () => this.setState({ currentTitle }));
  },

  getContent() {
    return (
      <div>
        Command: { this.data.post.title }
        <br />
        Stdout: { this.data.post.body }
        <br />
        Time: { this.data.post.createdAt.toString() }
      </div>
    );
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

    return (
      <div className="container-fluid text-center">
        <Row>
          <div style={ containerStyle }>
            <Col sm={ 12 }>
              <h3 style={ contentHeaderStyle }>Interactive demo</h3>
              <FormInput
                tred={ this.state.tred }
                changeHandler={ this.handleChange }
                clickHandler={ this.handleClick }
                submitHandler={ this.handleSubmit }
              />
              <p></p>
              { this.data.post ? this.getContent() :
                ( this.state.currentTitle ? <Loading /> : '' )}
              <p></p>
              <FormOutput name={ this.state.tred } />
            </Col>
          </div>
        </Row>
      </div>
    );
  },
});

module.exports = Content;
