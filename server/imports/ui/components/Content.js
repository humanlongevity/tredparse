import React from 'react';
import { ReactMeteorData } from 'meteor/react-meteor-data';
import { Meteor } from 'meteor/meteor';
import { Col, Row } from 'react-bootstrap';
import Documents from '../../api/documents/documents';
import FormInput from './FormInput';
import FormOutput from './FormOutput';
import Settings from './Settings';
import Loading from './Loading';
import TredparseResults from './TredparseResults';
import { Treds } from './TredTable';

const Content = React.createClass({
  getInitialState() {
    return {
      currentTitle: '',
      bam: Settings.s3BAM,
      tred: Settings.tred,
      ref: Settings.ref,
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

  handleClick(bam, tred, ref) {
    this.setState({ bam, tred, ref });

    const cmd = `tred.py ${bam} --tred ${tred} --ref ${ref}`;
    const currentTitle = cmd;
    const method = `docker.${Settings.env}`;
    Meteor.call(method, { cmd },
      () => this.setState({ currentTitle }));
  },

  buildURL() {
    if (Settings.env === 'public') {
      return null;
    }

    const bam = this.state.bam;
    let sampleID;
    if (bam[0] === '@') {
      sampleID = bam.substring(1);
    } else {
      const basename = this.state.bam.split(/[\\/]/).pop();
      sampleID = basename.split('_')[0];
    }
    const tr = Treds[this.state.tred];
    const [chr, pos] = tr.repeat_location.split(':');
    const [start, end] = pos.split('-');
    const mid = Math.round((+start + +end) / 2);
    const url = `https://search.hli.io/pileup/${sampleID}/${chr}/${mid}`;
    return url;
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

    const color = (Settings.env === 'public') ? 'green' : 'lightslategray';

    return (
      <div className="container-fluid text-center">
        <Row>
          <div style={ containerStyle }>
            <Col sm={ 12 }>
              <h3 style={ contentHeaderStyle }>Interactive STR server (
                <span style={{ color, fontWeight: 'bold' }}>{ Settings.env }</span>)
              </h3>
              <FormInput
                tred={ this.state.tred }
                changeHandler={ this.handleChange }
                clickHandler={ this.handleClick }
                submitHandler={ this.handleSubmit }
              />
              <p></p>
              {
                this.data.post ?
                  <TredparseResults
                    content={ this.data.post.body }
                    tred={ this.state.tred }
                  /> : (this.state.currentTitle ? <Loading /> : '')
              }
              <p></p>
              {
                this.state.tred ?
                <FormOutput name={ this.state.tred } url={ this.buildURL() } /> : null
              }
            </Col>
          </div>
        </Row>
      </div>
    );
  },
});

module.exports = Content;
